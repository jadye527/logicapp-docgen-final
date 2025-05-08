param (
    [Parameter(Mandatory = $true)]
    [object]$UserEmail,
    [Parameter(Mandatory = $true)]
    [object]$ManagerMail,
    [Parameter(Mandatory = $false)]
    [string]$WorkflowRunId = $null
)

# Initialize results object with workflow-compatible structure
$results = @{
    status = "Completed"  # Default to Completed, will change to Failed if issues occur
    workflowRunId = $WorkflowRunId
    output = @{
        mailboxConversion = @{
            success = $false
            details = ""
        }
        delegation = @{
            success = $false
            details = ""
        }
    }
    errors = @()
}

# Function to write formatted output for workflow consumption
function Write-WorkflowOutput {
    param (
        [Parameter(Mandatory = $true)]
        [object]$Results
    )
    
    # Convert to JSON and output it
    $jsonOutput = ConvertTo-Json -InputObject $Results -Depth 5 -Compress:$false
    Write-Output $jsonOutput  # Direct JSON output
}

# Suppress AzContext autosave
Disable-AzContextAutosave -Scope Process | Out-Null

try {
    # Step 1: Connect to Exchange Online using the managed identity
    Connect-ExchangeOnline -ManagedIdentity -Organization rehlko.com | Out-Null
} catch {
    $results.status = "Failed"
    $results.errors += @{
        code = "ConnectionError"
        message = "Failed to connect to Exchange Online: $_"
    }
    Write-WorkflowOutput -Results $results
    exit
}

# Step 2: Check if mailbox exists before proceeding
try {
    $mailbox = Get-Mailbox -Identity $UserEmail -ErrorAction Stop
    if ($null -eq $mailbox) {
        $results.status = "Failed"
        $results.errors += @{
            code = "MailboxNotFound"
            message = "Mailbox not found for $UserEmail"
        }
        Write-WorkflowOutput -Results $results
        exit
    }
} catch {
    $results.status = "Failed"
    $results.errors += @{
        code = "MailboxNotFound"
        message = "Failed to find mailbox: $_"
    }
    Write-WorkflowOutput -Results $results
    exit
}

# Step 3: Convert Mailbox to Shared with verification and retry logic
try {
    # Get mailbox state before change
    $mailboxBefore = Get-Mailbox -Identity $UserEmail | Select-Object RecipientTypeDetails, ExchangeGuid
    $results.output.mailboxConversion.details = "Initial mailbox type: $($mailboxBefore.RecipientTypeDetails)"
    
    # Convert Mailbox to Shared
    Set-Mailbox -Identity $UserEmail -Type Shared -ErrorAction Stop | Out-Null
    
    # Verification with retry logic
    $maxRetries = 3
    $retryCount = 0
    $conversionVerified = $false
    $retryDelay = 20  # seconds between retries

    while (-not $conversionVerified -and $retryCount -lt $maxRetries) {
        $retryCount++
        Start-Sleep -Seconds $retryDelay
        
        $mailboxAfter = Get-Mailbox -Identity $UserEmail | Select-Object RecipientTypeDetails
        
        if ($mailboxAfter.RecipientTypeDetails -eq "SharedMailbox") {
            $conversionVerified = $true
            $results.output.mailboxConversion.success = $true
            $results.output.mailboxConversion.details += " | Conversion to shared mailbox successful and verified on attempt $retryCount."
        } else {
            $results.output.mailboxConversion.details += " | Verification attempt $retryCount : mailbox is still type: ${mailboxAfter.RecipientTypeDetails}"
        }
    }

    if (-not $conversionVerified) {
        $results.status = "Failed"
        $results.errors += @{
            code = "ConversionVerificationFailed"
            message = "Mailbox conversion verification failed after $maxRetries attempts for $UserEmail"
        }
    }
} catch {
    $results.status = "Failed"
    $results.errors += @{
        code = "ConversionError"
        message = "Failed to convert mailbox: $_"
    }
    $results.output.mailboxConversion.details += " | Error during conversion"
}

# Step 4: Delegate Mailbox to Manager with verification and retry logic
try {
    # Check existing permissions - suppress output with [void]
    $hasExistingPermissions = @(Get-MailboxPermission -Identity $UserEmail | 
        Where-Object { $_.User -like "*$ManagerMail*" -and $_.AccessRights -contains "FullAccess" }).Count -gt 0
    
    if ($hasExistingPermissions) {
        $results.output.delegation.success = $true
        $results.output.delegation.details = "Manager already has FullAccess permissions on this mailbox."
    } else {
        # Delegate Mailbox to Manager
        [void](Add-MailboxPermission -Identity $UserEmail -User $ManagerMail -AccessRights FullAccess -InheritanceType All -AutoMapping $false -ErrorAction Stop)
        
        # Verification with retry logic
        $maxRetries = 3
        $retryCount = 0
        $delegationVerified = $false
        $retryDelay = 15  # seconds between retries

        while (-not $delegationVerified -and $retryCount -lt $maxRetries) {
            $retryCount++
            Start-Sleep -Seconds $retryDelay
            
            $hasPermissions = @(Get-MailboxPermission -Identity $UserEmail | 
                Where-Object { $_.User -like "*$ManagerMail*" -and $_.AccessRights -contains "FullAccess" }).Count -gt 0
            
            if ($hasPermissions) {
                $delegationVerified = $true
                $results.output.delegation.success = $true
                $results.output.delegation.details = "Delegation successful and verified on attempt $retryCount."
            } else {
                $results.output.delegation.details += " | Verification attempt ${retryCount}: permissions not found"
            }
        }

        if (-not $delegationVerified) {
            $results.status = "Failed"
            $results.output.delegation.details += " | Delegation verification failed after $maxRetries attempts."
            $results.errors += @{
                code = "DelegationVerificationFailed"
                message = "Delegation verification failed for $UserEmail to $ManagerMail after $maxRetries attempts"
            }
        }
    }
} catch {
    $results.status = "Failed"
    $results.errors += @{
        code = "DelegationError"
        message = "Failed to delegate mailbox: $_"
    }
    $results.output.delegation.details = "Error during delegation"
}

# Output results in workflow-compatible format
Write-WorkflowOutput -Results $results