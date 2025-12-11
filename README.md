# interaktiv.gdpr

A general-purpose GDPR (General Data Protection Regulation) compliance package for Plone.

## Overview

`interaktiv.gdpr` provides tools and features to help manage GDPR-compliant data handling in Plone sites.
The package implements various mechanisms to support data protection requirements,
including controlled deletion workflows and audit logging.

## Features
Features can be enabled or disabled independently through the GDPR control panel.

### 1. Deletion Log

A comprehensive audit log that tracks all deletion activities on the site:

- **Complete audit trail**: Records all deletion operations including who deleted what and when
- **Status tracking**: Tracks the lifecycle of deletions (pending, deleted, withdrawn)
- **Status change history**: Records when and by whom the status was changed
- **Configurable display period**: Define how many days of log entries to display in the control panel
- **Sortable and searchable**: The log table supports sorting by date and searching entries

### 2. Marked Deletion

Instead of immediately deleting content, this feature allows marking content for deletion and moving it to a dedicated container. This provides:

- **Grace period before permanent deletion**: Content is moved to a special container instead of being deleted immediately
- **Configurable retention period**: Define how many days content remains in the container before automatic permanent deletion (when Cronjob added)
- **Review and recovery options**: Administrators can review marked items and withdraw deletions to restore content to its original location
- **Subobject tracking**: Tracks the number of subobjects affected by each deletion

## Installation

1. Add `interaktiv.gdpr` and dependencies to your buildout or in your mxdev.ini:

e.g. mxdev.ini
```ini
[interaktiv.framework]
url = https://code.interaktiv.de/interaktiv/interaktiv.framework.git
rev = v14.0.2
extras = test

[interaktiv.gdpr]
url = https://github.com/interaktivgmbh/interaktiv.gdpr.git
rev = [CURRENT_VERSION]
extras = test
```

2. Run Your Buildout or App and install the package through Plone's Add-ons control panel or via Generic Setup profile.
3. (Optional) Add a Cronjob if you want automatic Deletion for on period of time. e.g.
gdpr_scheduled_deletion.py
```python
from interaktiv.gdpr.deletion_log import DeletionLog

deleted_count = DeletionLog.run_scheduled_deletion()
```

## License

GPL version 2

## Support

For issues, questions, or contributions, please contact the development team.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
