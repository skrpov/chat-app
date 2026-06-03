## What 

Chat app to learn django websockets / channels fundamentals for a more interesting project.

## Building

- Docker version >= 20

```sh
docker compose up --build
```

## Scope 
- Have users
- Have rooms, maybe with the rooms having permissions
- Have a telegram-like UI for choosing rooms 
- Have and a quick and dirty login flow 
- Have some kind of messsage types, maybe implement a "read" indicator since a real chat app would need something like this.

![Flow diagram](<docs/flow_diagram.png>)

## Tasks 
- [x] Make messages persist
- [x] Make sure that the client is able to view room history, not just the newest messages
    - [x] Send only a most recent window of history, and send more on request.
- [x] Dockerize the application and add running instructions
- [x] Ensure that on the client messages appear in the same order they were sent in
- [x] Make messages send to all connections, not just the sender.
- [x] Add a placeholder for when a room has no messages
- [x] Add join notification message
- [x] Add authentication
    - [x] Add a way to signup
    - [x] Add a way to login
    - [x] Ensure that pages other then login and signup redirect on unauthenticated access
    - [x] Display logged in user name in chat UI
- [x] Add rooms 
    - [x] No rooms yet placeholder
    - [x] Switching rooms closes the connection to current room before opening another
    - [x] Adding a new room makes it correctly show up in the room list
    - [x] Selected room is highlighted in the room list
    - [x] Room list order is sorted
    - [x] Room settings are only visible to room owner
    - [x] Room name correctly shows up in the chat view
    - [ ] Room name can be changed.
    - [x] Navigating to a room that isn't saved saves that room for the user.
    - [ ] User can un-save a room
- [x] Add room permissions
    - [x] Owners can own a room
    - [x] Rooms can be made public
        - [x] Room owner can add other users to a blacklist
    - [x] Rooms can be made private
      - [x] Room owner can add other users to a whitelist
- [ ] Secure redis so that it does not accept connections from other sources.
- [x] Add re-connect behaviour in case of browser closing the connection or server dropping or else.
- [ ] Add hamburger menu for group list page s.t. the chat is more usable on mobile.
- [ ] Add a landing page instead of just redirecting to login page right off the bat.
- [ ] Add some kind of message encryption / hashing
- [ ] Add a "delievered" indicator
- [ ] Add a "read" indicator
- [ ] Host the messenger on the WWW
- [ ] Only new message send time when the time is significantly different
- [ ] Dark mode / Global styles
- [ ] Some kind of spam protection


## References

- https://www.w3schools.com/django/index.php
- https://www.geeksforgeeks.org/python/learn-to-use-websockets-with-django/
- https://channels.readthedocs.io/en/latest/tutorial/part_2.html
- https://www.docker.com/blog/how-to-dockerize-django-app/
- https://github.com/jpadilla/django-project-template/blob/master/.gitignore