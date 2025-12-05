# interaktiv.gdpr

A general-purpose GDPR (General Data Protection Regulation) compliance package for Plone.

## Overview

`interaktiv.gdpr` provides tools and features to help manage GDPR-compliant data handling in Plone sites.
The package implements various mechanisms to support data protection requirements,
including controlled deletion workflows and audit logging.

## Features

### 1. Audit Deletion

Instead of immediately deleting content, this feature allows marking content for deletion and moving it to a dedicated container. This provides:

- **Grace period before permanent deletion**: Content is moved to a special container instead of being deleted immediately
- **Review and recovery options**: Administrators can review marked items before final deletion
- **Audit trail**: All deletion operations are tracked, logged and visible on a Controlpanel

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

## License

GPL version 2

## Support

For issues, questions, or contributions, please contact the development team.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
