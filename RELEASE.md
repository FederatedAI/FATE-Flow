## Release 2.1.0
### Major Features and Improvements
Improved the display issue of output data.
Enhanced the PyPI package: configuration files have been relocated to the user's home directory, and the relative paths for uploading data are based on the user's home directory.
Supported running FATE algorithms in Spark on YARN client mode.

### Bug-Fix
Fixed an issue where failed tasks could not be retried.
Fixed an issue where the system couldn't run when the task cores exceeded the system total cores.

## Release 2.0.0
### Major Features and Improvements
* Adapted to new scalable and standardized federated DSL IR
* Built an interconnected scheduling layer framework, supported the BFIA protocol
* Optimized process scheduling, with scheduling separated and customizable, and added priority scheduling
* Optimized algorithm component scheduling，support container-level algorithm loading， enhancing support for cross-platform heterogeneous scenarios
* Optimized multi-version algorithm component registration, supporting registration for mode of components
* Federated DSL IR extension enhancement: supports multi-party asymmetric scheduling
* Optimized client authentication logic, supporting permission management for multiple clients
* Optimized RESTful interface, making parameter fields and types, return fields, and status codes clearer
* Added OFX(Open Flow Exchange) module: encapsulated scheduling client to allow cross-platform scheduling
* Supported the new communication engine OSX, while remaining compatible with all engines from FATE Flow 1.x
* Decoupled the System Layer and the Algorithm Layer, with system configuration moved from the FATE repository to the Flow repository
* Published FATE Flow package to PyPI and added service-level CLI for service management
* Migrated major functionality from FATE Flow 1.x
