// ============================================================
// PM2 Ecosystem Config for n8n
// ============================================================
// This file provides all environment variables that n8n workflows
// reference via $env.VARIABLE_NAME — without needing the paid
// n8n Variables feature.
//
// USAGE:
//   pm2 start ecosystem.config.js
//   pm2 restart n8n              (to pick up config changes)
//   pm2 logs n8n                 (view n8n logs)
//
// AFTER EDITING entities.json:
//   pm2 restart n8n              (PM2 re-reads this file on restart,
//                                 which re-reads entities.json)
// ============================================================

const path = require('path');
const fs = require('fs');

// Auto-load entities config from the JSON file
// Edit config/entities.json directly — changes take effect on pm2 restart
const entitiesPath = path.join(__dirname, '..', 'config', 'entities.json');
let entitiesJson = '[]';
try {
  const entitiesFile = require(entitiesPath);
  entitiesJson = JSON.stringify(entitiesFile.entities || []);
} catch (e) {
  console.error('WARNING: Could not load entities.json from', entitiesPath);
  console.error('Entity lookup will not work until this is fixed.');
}

// Auto-load Google service account key from JSON file
// Place your service account key at: config/google-service-account.json
// Share your Google Drive folders with the service account email (client_email in the JSON)
const saPath = path.join(__dirname, '..', 'config', 'google-service-account.json');
let googleServiceAccountJson = '';
try {
  googleServiceAccountJson = fs.readFileSync(saPath, 'utf8').trim();
} catch (e) {
  console.error('WARNING: Could not load google-service-account.json from', saPath);
  console.error('Google API calls (Gemini, Drive, Docs) will not work until this is fixed.');
}

module.exports = {
  apps: [{
    name: 'n8n',
    script: 'n8n',
    args: 'start',
    // Restart on crash, max 10 restarts in 60 seconds
    max_restarts: 10,
    min_uptime: '60s',
    // Set all env vars here — n8n reads these via $env.VARIABLE_NAME
    env: {
      // ---- API Credentials ----
      // Monday.com: Your personal API token
      // Get it: monday.com → Avatar → Developers → My Access Tokens → "API v2 Token"
      MONDAY_API_TOKEN: 'CONFIGURE_ME',

      // DrChrono: OAuth2 bearer token
      // Get it: DrChrono → API settings → Generate token
      DRCHRONO_API_TOKEN: 'CONFIGURE_ME',

      // Google Cloud: Service account key (auto-loaded from file)
      // Place the JSON key file at: config/google-service-account.json
      // Required roles: Vertex AI User, Drive API, Docs API
      // Share Drive folders with the service account's client_email
      GOOGLE_SERVICE_ACCOUNT_JSON: googleServiceAccountJson,

      // ---- Google Cloud ----
      GCP_PROJECT_ID: 'CONFIGURE_ME',

      // ---- Google Drive Folder IDs ----
      // Get these from the folder URL: https://drive.google.com/drive/folders/<THIS_IS_THE_ID>
      GOOGLE_DRIVE_FOLDER_ID: 'CONFIGURE_ME',                  // Appeal Letters folder
      GOOGLE_DRIVE_DENIAL_INBOX_ID: 'CONFIGURE_ME',            // Denial Inbox folder
      GOOGLE_DRIVE_PROCESSED_DENIALS_ID: 'CONFIGURE_ME',       // Processed Denials folder
      GOOGLE_DRIVE_FAILED_DENIALS_ID: 'CONFIGURE_ME',          // Failed Denials folder

      // ---- RingCentral ----
      RINGCENTRAL_WEBHOOK_DENIALS: 'CONFIGURE_ME',

      // ---- DrChrono ----
      DRCHRONO_API_URL: 'https://app.drchrono.com/api',

      // ---- Entity Config ----
      // Auto-loaded from config/entities.json (no manual paste needed)
      // Edit that file directly, then run: pm2 restart n8n
      ENTITIES_CONFIG: entitiesJson,

      // ---- n8n Settings ----
      N8N_PORT: 5678,
      N8N_PROTOCOL: 'https',
      WEBHOOK_URL: 'https://CONFIGURE_YOUR_DOMAIN/n8n/',
      N8N_ENCRYPTION_KEY: 'CONFIGURE_ME',
      GENERIC_TIMEZONE: 'America/New_York',
    }
  }]
};
