# .bashrc
export JAVA_HOME=/opt/jdk-17
export PATH=$PATH:$JAVA_HOME/bin

# User specific aliases and functions

alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
