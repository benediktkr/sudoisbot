@Library('shared-jenkins-pipelines') _

poetry(
    //push_git_tag: true,

    docker: true,
    dockreg: "git.sudo.is/ben",

    // default: "pypi"
    pip_registry_name: "gitea",
    pip_publish: true,
    // not used:
    pip_registry_url: "https://git.sudo.is/api/packages/ben/pypi"
)
