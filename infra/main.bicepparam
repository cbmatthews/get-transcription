using 'main.bicep'

param appName = 'prism'
param staticWebAppLocation = 'eastus2'

// M0 ships with fake providers. M1 switches transcription to 'azure-speech-fast';
// M3 switches generation to 'azure-openai'.
param transcriptionProvider = 'fake'
param generationProvider = 'fake'

// deployerPrincipalId is passed by scripts/deploy.sh (your signed-in user's object ID).
