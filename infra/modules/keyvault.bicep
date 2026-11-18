// Key Vault (RBAC mode). V1 secrets that can't use managed identity live here,
// e.g. the Notion integration token in M5.
param location string
param name string
param functionPrincipalId string
param deployerPrincipalId string
param tags object

var roles = {
  secretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  secretsOfficer: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
}

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

// Non-sensitive canary the /api/health check reads to prove the managed identity
// can reach Key Vault.
resource healthSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'prism-healthcheck'
  properties: {
    value: 'ok'
    contentType: 'text/plain'
  }
}

resource functionSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, functionPrincipalId, roles.secretsUser)
  scope: vault
  properties: {
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.secretsUser)
  }
}

resource deployerSecretsOfficer 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(vault.id, deployerPrincipalId, roles.secretsOfficer)
  scope: vault
  properties: {
    principalId: deployerPrincipalId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.secretsOfficer)
  }
}

output name string = vault.name
output uri string = vault.properties.vaultUri
