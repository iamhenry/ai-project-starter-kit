---
name: plan
description: Read-only analysis and planning agent with safe bash commands and web search.
mode: primary
model: openai/gpt-5.6-sol
variant: medium
tools:
  write: false
  edit: false
  read: true
  grep: true
  glob: true
  list: true
  bash: true
  webfetch: true
  websearch: true
  todowrite: true
  todoread: true
permission:
  edit: deny
  bash:
    "rmdir *": deny
    "mv *": deny
    "sudo *": deny
    "dd *": deny
    "mkfs*": deny
    "chmod -R*": deny
    "chown -R*": deny
    "> *": deny
    "cat *": deny
    "*<<*": deny
    "truncate *": deny
    "git reset*": deny
    "git clean*": deny
    "git rebase*": deny
    "git branch -D*": deny
    "git reflog expire*": deny
    "git update-ref*": deny
    "git merge*": deny
    "git pull*": deny
    "git checkout*": deny
    "git switch*": deny
    "git restore*": deny
    "git add*": deny
    "git rm*": deny
    "gh pr checkout*": deny
    "gh pr update-branch*": deny
    "gh pr create*": deny
    "gh pr merge*": deny
    "gh pr close*": deny
    "gh pr edit*": deny
    "gh pr reopen*": deny
    "gh pr ready*": deny
    "gh pr review*": deny
    "gh pr comment*": deny
    "gh pr lock*": deny
    "gh pr unlock*": deny
    "gh repo clone*": deny
    "gh repo create*": deny
    "gh repo delete*": deny
    "gh repo fork*": deny
    "gh repo sync*": deny
    "npm install*": deny
    "git commit*": ask
    "git push*": ask
    "rm *": ask
    "*": allow
  webfetch: allow
---

Read-only analysis and planning agent. Do not edit files. Use Read instead of cat.
