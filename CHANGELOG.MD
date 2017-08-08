# Change Log

## [3.0.2]
### Fixed 
- extract_keys Command in django >= 1.10 (Thanks, nanorepublica)

## [3.0.1]
### Fixed
-  Default installation version

## [3.0-a8]
### Changed
-  The message trim length can now be defined in the settings, see #4 for more details.
### Added
-  The region can now be defined in the settings

## [3.0-alpha7]
### Changed
-  Formatting issues and proper Changelog introduction

### Fixed
-  Python 2.7 Support

### Removed
-  Python 2.6 Support

## [3.0-alpha2] - [3.0-alpha6]
### Fixes
-  Various bugfixes

## [3.0-alpha1]
### Removed
-  Dismissed South support

### Changed
-  Platforms etc. are now handled with models

## [2.0-alpha2] - 2015-09-24
### Added
-  Django >= 1.7 support (migrations)

## [2.0-alpha] - 2015-07-01
### Added
-  Added the ability to use arn directly for instancing an application.

## [1.1] - 2015-07-01
### Changed
-  Improving SNSDevice.register_or_update function: The function raises now an exception if the error when creating the
ARN is not the 'already exists'-exception


## [1.0.3] - 2015-01-06
### Changed
-  Improving the create_or_update SNSDevice method: If the device is already registered with other attributes, the
given error gets parsed an updated with the new attributes.

## [1.0.2] - 2015-01-06
### Changed
-  The PushMessage model allows now more null values

## [1.0.1] - 2015-01-06
### Added
-  Python 3 support
-  Logging settings

### Changed
- Documentation

## [1.0] - 2015-01-05
### Changed
-  Initial release



