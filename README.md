reppo
=====

Lightweight Github-style repo viewer using Flask and libgit2

Story so far
------------

Reppo gives your git repos what is essentially a cut-back version of the github UI. It supports the tree, commit, commits, blob, raw, blame* and contributors* pages that github offers.

* blame and contributors are totally prototype for the former and really basic for the latter.

It has been tested with the following types of repository:

* Bare repo with ~11,000 commits, ~3,100 branches and ~50 contributors
* Local repo (created with `git init`) with < 10 branches and 1 contributor

It has *not* been tested with a completely remote repo or repos that do not use a commit-rebase-push approach to branching.

Setup
-----

Once you have cloned the repo, either create a virtualenv or be prepared to stomp over your global python libs. Whatever your preference.

Whatever you do, do *NOT* do anything with setup.py. At this point, setup.py is a lie, fit only for telling you the dependencies of the project as they currently stand.

With that in mind, open up setup.py and install the dependencies manually through pip, _except_ pygit2.

pygit2
------

To install pygit2, follow the guide at http://www.pygit2.org/install.html - at this time, we're using the latest version (v0.21.4) available.

Configuration and Running
-------------------------

Changes you will more than likely need to make are in *conf/uwsgi.conf*. It should be obvious which values will need altering (or in the case of virtualenv, removing if you're not using virtualenv).

To configure exposed git repos for viewing within Reppo, you will need to modify the *REPOS* value inside *reppo/reppo/defaults.py*

There is a terribly-written bash script in the root called *uwsgi-reppo* which can start, stop and reload the Reppo instance. It has no checks for ensuring only one instance is running, so running "start" multiple times will keep spawning new instances of Reppo, whereas "stop" will only stop the last instance the process file points to.

I told you it was terrible.

To run manually, you can use the *manage* script in the repo root. There are two commands that *manage* accepts -- *shell* and *runserver*. They should be self-explanatory.

Problems?
---------

Let me know (maybe create an issue?). Problems with getting pygit2 installed are expected and should be viewed as a badge of honour if it installs first time with no problem.
