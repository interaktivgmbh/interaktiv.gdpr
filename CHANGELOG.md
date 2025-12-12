# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-12

### Added

- Marked Deletion feature: soft-delete mechanism that moves objects to a container instead of immediate deletion
- Configurable retention period before permanent deletion (default: 30 days)
- Automatic scheduled deletion via `DeletionLog.run_scheduled_deletion()` for cronjob integration
- Deletion Log with complete audit trail (user, timestamp, object details, workflow state)
- Status tracking for deleted objects: `pending`, `deleted`, `withdrawn`
- Control panel at `@@interaktiv-gdpr-controlpanel` with settings and deletion overview
- REST API endpoints:
  - `@gdpr-withdraw-deletion/{uid}` - restore objects to original location
  - `@gdpr-permanent-deletion/{uid}` - immediate permanent deletion
  - `@gdpr-settings` - GET/PATCH settings
  - `@gdpr-deletion-log` - GET deletion log
- MarkedDeletionContainer content type with dedicated workflow
- Access control via traversers for browser and REST API requests
- Permissions: `ViewControlpanel`, `ViewDeletionInfoSettings`, `AddMarkedDeletionContainer`
- German and English language support
