# sudoisbot

[![Build Status](https://jenkins.sudo.is/buildStatus/icon?job=ben%2Fsudoisbot%2Fmain&style=flat-square)](https://jenkins.sudo.is/job/ben/job/sudoisbot/job/main/)
[![git](https://img.shields.io/website?label=git&up_message=ben%2Fsudoisbot&url=https%3A%2F%2Fgit.sudo.is%2Fben%2Fsudoisbot)](https://git.sudo.is/ben/sudoisbot)
[![github](https://img.shields.io/website?label=github&up_message=ben%2Fsudoisbot&url=https%3A%2F%2Fgithub.com%2Fbenediktkr%2Fsudoisbot&color=orange)](https://github.com/benediktkr/sudoisbot)
![matrix](https://img.shields.io/static/v1?label=matrix&message=%23darkroom:sudo.is&color=purple&style=flat-square)

this is a home monitoring system written in python and using
[zmq](https://www.zeromq.org).

![sudoisbot in grafna](docs/img/sudoisbot-grafana.png)

## related projects

 * [zflux](https://git.sudo.is/ben/zflux): a buffering proxy (using
 zmq) to gracefully handle network failures, and can also do load
 balancing.


## architecture

  * proxy
  * sink
  * sensor
  * apis


# license

GPL
