# Yt-Post-Notifier
A small python script to check whether certain YouTube channels posted new community posts and notify you accordingly.

## Normal Usage
The script can be started using this syntax:

Linux/OsX:
```bash
./launch-unix run <MODE>
```
Windows:
```cmd
launch-windows.bat run <MODE>
```

For explaination on the `<MODE>` argument, have a look at the [execution modes](#execution-modes)

The script exists with exit code 1 if no new post was found. Post 0 indicates that at least one notification was sent.

> [!IMPORTANT]
> When calling the script for the first time, it will create a configuration file and then exist so you can configure it the way you want.

## Execution Modes
This tool can be executed in two modes:

|             | check_unvisited | check_unread |
| ----------- | --------------- | ------------ |
| **Description** | Looks for newly posted posts | Looks for posts the user hasn't explicitely acknowledged |
| **Details** | If the YouTube channel posted something new, this will identity that post. If the post is old (has already benn indexed), no notification will be sent | If the YouTube channel posted something new, this will identity the post. If the post is old (has already benn indexed) but the user has not clicked the "Open Posts" or "Mark As Read" button, a notification will be sent |
| **Advantage** | Notifies you only once per post | Enables you to check whether you have missed a post notification |
| **Disadvantage** | When not at the PC, you might miss a post notification without noticing | Might motify you multiple times per post |
| **Typical use case** | Actively monitoring notifications while duplicates | Safety net to ensure no posts are overlooked, even if you miss a notification |


## Configuration
This script stores its notifications in a folder named **yt-post-notifier** in your system's configuration path.

<details>
    <summary>Config File Schema</summary>

    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "users": {
                "type": "array",
                "description": "List of YouTube accounts to check when looking for new community posts. Each entry can be an object with settings or just a string representing the user_name.",
                "items": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "user_name": {
                                    "type": "string",
                                    "description": "The YouTube user name of the account (can be found in the account URL but without the leading \"@\")"
                                },
                                "display_name": { 
                                    "type": "string",
                                    "default": "${user_name}",
                                    "description": "The name to use when displaying the account's name. This does NOT have to be the YouTube user name but is for display purposes only"
                                },
                                "icon": { 
                                    "type": "string",
                                    "default": null,
                                    "description": "A URI to the image file to use as icon when displaying the notification"
                                },
                                "sound": { 
                                    "type": "string",
                                    "default": "${system_default_sound}",
                                    "description": "A URI to the auio file to use as sound when displaying the notification"
                                },
                                "title_text": { 
                                    "type": "string",
                                    "default": "${NAME} posted!",
                                    "description": "The text to use as title of the notification. The placeholder \"${NAME}\" will expand to the user's display_name and \"${POST}\" will become the content of the newest post. By adding a positive integer argument to the post placeholder (eg \"${POST;10}\"), the post will be trimmed to max n characters. \"${COUNT}\" will expand to the amount of new posts and \"${PLURAL_S}\" will be either an \"s\" if the count is more than 1, otherwise it will be empty"
                                },
                                "message_text": { 
                                    "type": "string",
                                    "default": "${NAME} posted a new community post: ${POST;100}",
                                    "description": "The text to use as message content of the notification. The placeholder \"${NAME}\" will expand to the user's display_name and \"${POST}\" will become the content of the newest post. By adding a positive integer argument to the post placeholder (eg \"${POST;10}\"), the post will be trimmed to max n characters. \"${COUNT}\" will expand to the amount of new posts and \"${PLURAL_S}\" will be either an \"s\" if the count is more than 1, otherwise it will be empty"
                                },
                                "duration": { 
                                    "type": "integer",
                                    "default": -1,
                                    "description": "The display duration of the notification in seconds where -1 is the default notification duration of your system. When setting this to 0 or a value below -2, the behavior is unspecified and depends on the notification handler"
                                },
                                "urgency": { 
                                    "type": "integer",
                                    "enum": [-1, 0, 1],
                                    "default": 0,
                                    "description": "The urgency of the notification where -1 is low, 0 is normal and 1 is critical"
                                }
                            },
                            "required": ["user_name"],
                            "additionalProperties": false
                        },
                        {
                            "type": "string",
                            "description": "The YouTube user name of the account (can be found in the account URL but without the leading \"@\"). This is a shortcut for the user object and will set all other configuration fields of this user to their default value"
                        }
                    ]
                }
            },
            "notification_timeout": { 
                "type": "integer",
                "default": 15,
                "description": "The timeout after which unresponded notifications will be discarded in seconds"
            },
            "internal_post_display": { 
                "type": "boolean",
                "default": true,
                "description": "Whether to open the post page of YouTube users in a custom browser window. When this is set to false, the page will be opened in the default browser"
            }
        },
        "additionalProperties": false
    }
</details>

<details>
    <summary>Config File Example</summary>

    {
        "users": [
            {
                "user_name": "johndoe42",
                "display_name": "John Doe",
                "icon": "/home/user/Images/john.png",
                "sound": "/home/user/Audio/notification.ogg",
                "title_text": "${NAME}: '${POST;10}'",
                "message_text": "Fount ${COUNT} new post${PLURAL_S} by ${NAME} and with the content '${POST}'",
                "duration": 10,
                "urgency": 1
            },
            "janedoe37"
        ],
        "notification_timeout": 20,
        "internal_post_display": false,
    }

</details>
<p>

For information on the different config properties, have a look at the _description_ tags in the config schema.

## Testing

This tool comes with some in-built testing tools that allow you to actively run specific parts of the tool workflow for debug purposes by adding the "test" argument in the command line. These tools are:

- `test dump_config`

    Loads the tool configuration, initilizeses defaults where needed and prints the whole config object in a JSON format

- `test scrape <USER_NAME>`

    Prints the last posts of USER_NAME in a JSON format where USER_NAME is the YouTube user name of the account

- `test notify <USER_NAME> <POST> <COUNT>`

    Sends a test notification that USER_NAME posted COUNT new posts with content POST; making use of the user's notification configuration

- `test display <USER_NAME>`

    Shows USER_NAME's posts using the display method specified in the config

## Dependencies

🔵 `python3`

The script depends on the following 3rd-part packages:

- [`urllib3`](https://pypi.org/project/urllib3/)
- [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)
- [`platformdirs`](https://pypi.org/project/platformdirs/)
- [`desktop-notifier`](https://pypi.org/project/desktop-notifier/)
- When using _internal_post_display_: [`pywebview`](https://pypi.org/project/pywebview/)


## Scheduled execution

For a notificator script like this, it makes sense to run it using a scheduled service. Since the purpose of this script is not to be an always-running background task, you are strongly encouraged to setup a scheduled execution for this using an OS service or similar method

## License

This project is licensed under the [MIT License](./LICENSE)
