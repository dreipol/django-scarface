# -*- coding: utf-8 -*-
import logging

from django.db.models.signals import  post_delete
from django.dispatch import receiver

from scarface.models import Device, Platform, Topic, Subscription

__author__ = 'janmeier'

logger = logging.getLogger('django_scarface')

@receiver(post_delete, sender=Device)
@receiver(post_delete, sender=Platform)
@receiver(post_delete, sender=Topic)
@receiver(post_delete, sender=Subscription)
def device_deleted(sender, instance, **kwargs):
    if not instance.deregister():
        logger.warn("Could not unregister device on delete.")
