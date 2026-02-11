---
description: Tool for updating context bank with recent Git changes and explanations
alwaysApply: false
---

<UpdateContext>
  1. run a git command to get the recent changes (`git log main..HEAD --pretty=format:"%h | %ad | %s%n%b" --date=format:"%I:%M %p %b %d, %Y"`)
  2. Include the changes but also explain why we made those decisions
  3. Ensure to grab the date and timestamp from the git commit to use them in the changelog (eg. format: Feb 2, 2025, 2:45PM). 
  4. IMPORTANT:Append files in `Context Bank` directory and ensure to respect the format structure. dont overwrite or mix previous days work with recent changes
</UpdateContext>