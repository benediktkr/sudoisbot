@Library('shared-jenkins-pipelines') _

poetry(
    //push_git_tag: true,

    docker: true,
    dockreg: "git.sudo.is/ben",

    pip_publish: true,
    // default: "pypi"
    pip_repo_name: "gitea",
    pip_repo_url: "https://git.sudo.is/api/packages/ben/pypi"
)
