param (
    [Parameter(Mandatory = $true)]
    [object]$UserEmail,
    [Parameter(Mandatory = $false)]
    [string]$WorkflowRunId = $null
)

# Initialize results object with workflow-compatible structure
$results = @{
    status = "Completed"  # Default to Completed, will change to Failed if issues occur
    workflowRunId = $WorkflowRunId
    output = @{
        groupRemoval = @{
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

try {
    # Connect to Active Directory using the managed identity
        # Ensure the Active Directory module is installed
        if (-not (Get-Module -ListAvailable -Name ActiveDirectory)) {
            Install-Module -Name ActiveDirectory -Force -Scope AllUsers -ErrorAction Stop
        }
        Import-Module ActiveDirectory -ErrorAction Stop

    # Get all groups the user is a member of
    $userADAccount = (Get-ADUser -Filter { UserPrincipalName -eq $UserEmail } -Property MemberOf)
    if (-not $userADAccount) {
        $results.status = "Failed"
        $results.errors += @{
            code = "UserNotFound"
            message = "Failed to find user: $UserEmail"
        }
        Write-WorkflowOutput -Results $results
        exit
    }

    $groups = $userADAccount.MemberOf

    if (-not $groups) {
        $results.output.groupRemoval.details = "User $UserEmail is not a member of any groups."
        $results.output.groupRemoval.success = $true
    } else {
        foreach ($group in $groups) {
            try {
                Remove-ADGroupMember -Identity $group -Members $userADAccount.SamAccountName -Confirm:$false
            } catch {
                $results.errors += @{
                    code = "GroupRemovalError"
                    message = "Failed to remove user from group $group : $_"
                }
                $results.status = "Failed"
            }
        }
        $results.output.groupRemoval.success = $true
        $results.output.groupRemoval.details = "Successfully removed user $UserEmail from all groups."
    }
} catch {
    $results.status = "Failed"
    $results.errors += @{
        code = "ScriptError"
        message = "An error occurred during execution: $_"
    }
}

# Output results in workflow-compatible format
Write-WorkflowOutput -Results $results
