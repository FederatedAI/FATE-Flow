## Release 2.0.0-beta
### Major Features and Improvements
* Migrated functions: data upload/download, process scheduling, component output data/model/metric management, multi-storage adaptation for models, authentication, authorization, feature anonymization, multi-computing/storage/communication engine adaptation, and system high availability
* Optimized process scheduling, with scheduling separated and customizable, and added priority scheduling
* Optimized algorithm component scheduling, dividing execution steps into preprocessing, running, and post-processing
* Optimized multi-version algorithm component registration, supporting registration for mode of components
* Optimized client authentication logic, supporting permission management for multiple clients
* Optimized RESTful interface, making parameter fields and types, return fields, and status codes clearer
* Decoupling the system layer from the algorithm layer, with system configuration moved from the FATE repository to the Flow repository
* Published FATE Flow package to PyPI and added service-level CLI for service management

## Release 2.0.0-alpha
### Feature Highlights
* Adapted to new scalable and standardized federated DSL IR
* Standardized API interface with param type checking 
* Decoupling Flow from FATE repository 
* Optimized scheduling logic, with configurable dispatcher decoupled from initiator
* Support container-level algorithm loading and task scheduling, enhancing support for cross-platform heterogeneous scenarios
* Independent maintenance for system configuration to enhance flexibility and ease of configuration
* Support new communication engine OSX, while compatible with all engines from Flow 1.X
* Introduce OFX(Open Flow Exchange) module: encapsulated scheduling client to allow cross-platform scheduling