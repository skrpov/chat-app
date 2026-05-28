## What 

Chat app to learn django websockets / channels fundamental for a more interesting project.

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
    - [ ] Send only a most recent window of history, and send more on request.
- [x] Dockerize the application and add running instructions
- [ ] Ensure that on the client messages appear in the same order they were sent in
- [x] Make messages send to all connections, not just the sender.
- [x] Add authentication
    - [x] Add a way to signup
    - [x] Add a way to login
    - [x] Ensure that pages other then login and signup redirect on unauthenticated access
- [ ] Add rooms 
    - [ ] No rooms yet placeholder
    - [ ] Switching rooms closes the connection to current room before opening another
    - [ ] Adding a new room makes it correctly show up in the room list
    - [ ] Room list order is stable
    - [ ] Room settings are only visible to room owner
- [ ] Add room permissions
    - [ ] Owners can own a room
    - [ ] Rooms can be made public
        - [ ] Room owner can add other users to a blacklist
    - [ ] Rooms can be made private
      - [ ] Room owner can add other users to a whitelist
- [ ] Secure redis so that it does not accept connections from other sources.

## References

- https://www.w3schools.com/django/index.php
- https://www.geeksforgeeks.org/python/learn-to-use-websockets-with-django/
- https://channels.readthedocs.io/en/latest/tutorial/part_2.html
- https://www.docker.com/blog/how-to-dockerize-django-app/
- https://github.com/jpadilla/django-project-template/blob/master/.gitignore