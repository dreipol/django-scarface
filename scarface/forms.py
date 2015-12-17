# -*- coding: utf-8 -*-
from django import forms

from scarface.models import Platform
from scarface.platform_strategy import get_strategies, get_strategy_choices

__author__ = 'janmeier'

class PlatformAdminForm(forms.ModelForm):
    platform = forms.CharField(widget=forms.Select(
        choices=get_strategy_choices().items()
    ))

    class Meta:
        model = Platform
        exclude =[]
