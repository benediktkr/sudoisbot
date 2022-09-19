# sudoisbot

[![Build Status](https://jenkins.sudo.is/buildStatus/icon?job=ben%2Fsudoisbot%2Fmain&style=flat-square)](https://jenkins.sudo.is/job/ben/job/sudoisbot/)
[![git](docs/img/shields/git.sudo.is-ben-sudoisbot.svg)](https://git.sudo.is/ben/sudoisbot)
[![github](https://git.sudo.is/ben/infra/media/branch/main/docs/img/shields/github-benediktkr.svg)](https://github.com/benediktkr/sudoisbot)
[![matrix](https://git.sudo.is/ben/infra/media/branch/main/docs/img/shields/darkroom.svg)](https://matrix.to/#/#darkroom:sudo.is)

this is a home monitoring system written in python and using
[zmq](https://www.zeromq.org).

![sudoisbot in grafna](docs/img/sudoisbot-grafana.png)

## related projects

 * [zflux](https://git.sudo.is/ben/zflux): a buffering proxy (using
 zmq) to gracefully handle network failures, and can also do load
 balancing.

 * [shared-jenkins-pipelines](https://git.sudo.is/ben/shared-jenkins-pipelines):
 jenkins delcarative pipelines, including the
 [`poetry.groovy`](https://git.sudo.is/ben/shared-jenkins-pipelines/src/branch/main/vars/poetry.groovy)
 pipeline used to build this project.


## architecture

  * proxy
  * sink
  * sensor
  * apis


# license

GPL
