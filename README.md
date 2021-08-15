# Automated / CLI Canvas Conversations

This is a small CLI application that allows you to append messages to existing conversation threads on Instructure Canvas as well as schedule them using crontab.

![example of usage in Canvas](/imgs/canvas_example.png)

## Compatability

This application currently does not run properly on Windows devices, but compatability is a feature that will be looked into.

## Dependencies

```
pip install python-crontab colored argparse requests inquirer
```

## Install

Run the below command into any folder.

```
git clone https://github.com/blackboardd/automated-canvas-conversations.git
```

Do not forget to export your access token in ~/.bashrc.

## Troubleshooting

### Help, my messages aren't sending!
See what is happening in info.log

![example of usage in a terminal shell](/imgs/term_example.png)
