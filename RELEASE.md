## Release 2.0.0
### Major Features and Improvements
* Adapted to new scalable and standardized federated DSL IR
* Build an interconnected scheduling layer framework, support the BFIA protocol
* Optimized process scheduling, with scheduling separated and customizable, and added priority scheduling
* Optimized algorithm component scheduling，support container-level algorithm loading， enhancing support for cross-platform heterogeneous scenarios
* Optimized multi-version algorithm component registration, supporting registration for mode of components
* Federated DSL IR extension enhancement: supports multi-party asymmetric scheduling.
* Optimized client authentication logic, supporting permission management for multiple clients
* Optimized RESTful interface, making parameter fields and types, return fields, and status codes clearer
* Introduce OFX(Open Flow Exchange) module: encapsulated scheduling client to allow cross-platform scheduling
* Support new communication engine OSX, while compatible with all engines from Flow 1.X
* Decoupling the system layer from the algorithm layer, with system configuration moved from the FATE repository to the Flow repository
* Published FATE Flow package to PyPI and added service-level CLI for service management
* Major functionality migration from FATE Flow v1
