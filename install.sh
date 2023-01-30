#!/bin/zsh
cp -r "Log Current Focus.app" ~/Applications/.
cp edu.brown.ccv.jholla10.log-focus-every-5-minutes.plist ~/Library/LaunchAgents/.
launchctl load -w ~/Library/LaunchAgents/edu.brown.ccv.jholla10.log-focus-every-5-minutes.plist