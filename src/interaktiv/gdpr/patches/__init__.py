from interaktiv.gdpr.patches import manage_del_objects


def apply_patches():
    manage_del_objects.apply_patch()


apply_patches()
