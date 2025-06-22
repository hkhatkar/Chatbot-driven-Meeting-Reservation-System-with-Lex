import 'regenerator-runtime/runtime';
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ConfigContext } from './ConfigContext';
import { Amplify, Interactions } from 'aws-amplify'
import AWSLex2Provider from '@thefat32/aws-amplify-lex-provider-v2'


Amplify.addPluggable(new AWSLex2Provider())


async function bootstrap() {
  // 1) Load the runtime config that CDK just deployed
  const res = await fetch('/config.json');
  if (!res.ok) {
    throw new Error(`Failed to load /config.json: ${res.status} ${res.statusText}`);
  }
  const cfg = await res.json();

  //Configure Amplify (including Interactions)
  Amplify.configure({
    Auth: {
      identityPoolId: cfg.identityPoolId,
      region: cfg.lexBotRegion,
    },
    Interactions: {
      bots: {
        [cfg.lexBotName]: {
          name: cfg.lexBotName,
          botAliasId: cfg.lexBotAliasId.split("|")[0],
          botId: cfg.lexBotId,
          localeId: cfg.lexBotLocaleId,
          region: cfg.lexBotRegion,
          providerName: "AWSLex2Provider"
        }
      }
    }
  });


  console.log("Registered bot config:", Amplify._config.Interactions.bots)


  createRoot(document.getElementById('root')).render(
    <ConfigContext.Provider value={cfg}>
    <StrictMode>
      <App />
    </StrictMode>
    </ConfigContext.Provider>
    
  );
}
bootstrap().catch(err => {
  console.error("Startup error:", err);
});