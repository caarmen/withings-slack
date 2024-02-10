# Architecture

The arrows in the architecture indicate dependencies. For example, the Domain layer depends on the Data layer.

## Overview
```mermaid
graph TD

    subgraph EntryPoints[Entry points]
        Routes
        Tasks
    end
    subgraph Domain
        UseCases
    end
    subgraph Data
        Database
        Repositories
    end
    subgraph RemoteServices[Remote services]
        Apis
    end

    EntryPoints-->Domain
    Domain-->Data
    Domain-->RemoteServices
```

## More detailed view
```mermaid
graph TD
    subgraph Main
    end
    subgraph Routes
        FitbitRoutes
        WithingsRoutes
    end
    subgraph Tasks
        FitbitPolling
    end
    subgraph Domain
        subgraph UseCases
            FitbitUseCases
            WithingsUseCases
            SlackUseCases
        end
    end
    subgraph Data
        Database
        subgraph Repositories
            FitbitRepository
            WithingsRepository
        end
    end
    subgraph RemoteServices[Remote services]
        FitbitApis
        WithingsApis
    end
    subgraph Core
        CoreModels[Models]
        Exceptions
    end
    subgraph OAuth
        FitbitOAuth
        WithingsOAuth
    end


    Main-->Routes
    Main-->Tasks
    Tasks-->Domain
    Routes-->Domain
    Repositories-->Database
    Domain-->Data
    Domain-->RemoteServices
    Domain-->Core
    RemoteServices-->Core
    RemoteServices-->OAuth
    Routes-->OAuth
```
