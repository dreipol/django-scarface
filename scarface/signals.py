# -*- coding: utf-8 -*-
import logging

from django.db.models.signals import  post_delete
from django.dispatch import receiver

from scarface.exceptions import SNSException
from scarface.models import Device, Platform, Topic, Subscription

__author__ = 'janmeier'

logger = logging.getLogger('django_scarface')

@receiver(post_delete, sender=Device)
@receiver(post_delete, sender=Platform)
@receiver(post_delete, sender=Topic)
@receiver(post_delete, sender=Subscription)
def instance_deleted(sender, instance, **kwargs):
    """
    Unregisters the instance from amazon sns.
    """
    try:
        if instance.is_registered and not instance.deregister(save=False):
            logger.warn("Could not unregister {0} on delete.".format(
                sender
            ))
    except SNSException:
        # Avoid that invalid arn token cause error when deleting instance
        pass
