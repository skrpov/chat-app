# Tasks

An index into the GitHub issues, which hold the descriptions and any notes on what
was actually implemented. Git history is authoritative on what is done.

## Messaging

- [x] Make messages persist
- [x] Make sure that the client is able to view room history, not just the newest messages
    - [x] Send only a most recent window of history, and send more on request.
- [x] Ensure that on the client messages appear in the same order they were sent in
- [x] Make messages send to all connections, not just the sender.
- [x] Add a placeholder for when a room has no messages
- [x] Add join notification message
- [x] Add re-connect behaviour in case of browser closing the connection or server dropping or else.
- [ ] Show profile pictures in the chat view (#3)
    - [ ] Send the sender's user id in the message packet (#4)
    - [ ] Take the display name from the authenticated user instead of the client packet (#5)
    - [ ] Render the avatar beside each message, falling back to the initial placeholder (#6)
    - [ ] Test the app still works end-to-end on dev server (#7)
    - [ ] Deploy profile pictures in chat to live server (#8)
- [ ] Rate limiting and spam protection (#9)
    - [ ] Limit how often one connection can send messages (#10)
    - [ ] Enforce the message length limit in the consumer (#11)
    - [ ] Throttle signup and login attempts (#12)
- [x] Add some kind of message encryption / hashing
    - [x] Encrypt message bodies at rest
    - [ ] End-to-end encryption so that the server operator cannot read messages (#13)
- [ ] Add a "delievered" indicator (#14)
- [ ] Add a "read" indicator (#15)
- [ ] Only new message send time when the time is significantly different (#16)
- [ ] Add image sending support (long-term) (#17)
- [ ] Bug: every message send runs a COUNT over the whole room (#18)
- [ ] Bug: the chat view loads every message in the database into a context the template never uses (#19)

## Rooms

- [x] Add rooms
    - [x] No rooms yet placeholder
    - [x] Switching rooms closes the connection to current room before opening another
    - [x] Adding a new room makes it correctly show up in the room list
    - [x] Selected room is highlighted in the room list
    - [x] Room list order is sorted
    - [x] Room settings are only visible to room owner
    - [x] Room name correctly shows up in the chat view
    - [x] Navigating to a room that isn't saved saves that room for the user.
    - [ ] Room name can be changed. (#20)
    - [ ] User can un-save a room (#21)
- [x] Add room permissions
    - [x] Owners can own a room
    - [x] Rooms can be made public
        - [x] Room owner can add other users to a blacklist
    - [x] Rooms can be made private
        - [x] Room owner can add other users to a whitelist
- [x] Make the room sidebar resizable / collapsible (mobile support)
- [x] Add hamburger menu for group list page s.t. the chat is more usable on mobile.
- [ ] Room visibility levels (#22)
    - [ ] Replace public and private with viewable by anyone, signed-in users, or invite only (#23)
        - [ ] Migrate existing rooms onto the new levels (#24)
        - [ ] Split the access check into view and post (#25)
        - [ ] Handle anonymous users in the access check (#26)
        - [ ] Update the room settings UI for the third level (#27)
    - [ ] Let anonymous users read rooms that anyone can view (#28)
        - [ ] Serve the chat view without requiring login for those rooms (#29)
        - [ ] Skip saving the room for anonymous visitors (#30)
        - [ ] Accept read-only websocket connections (#31)
        - [ ] Reject sends from anonymous users and prompt account creation (#32)
        - [ ] Handle the sidebar and header with no logged in user (#33)
- [ ] Explore and search (#34)
    - [ ] Search rooms by name or id (#35)
    - [ ] Explore page listing rooms that anyone can view (#36)
    - [ ] Onboarding path from a room into signup (#37)
- [ ] Show current room name in the browser tab title (#38)

## Accounts

- [x] Add authentication
    - [x] Add a way to signup
    - [x] Add a way to login
    - [x] Ensure that pages other then login and signup redirect on unauthenticated access
    - [x] Display logged in user name in chat UI
- [x] Add profile pictures
- [ ] Fix user signup flow (#39)
    - [ ] Add email field to signup (#40)
        - [ ] Need to delete old accounts that have no recovery method. (#41)
        - [ ] Create django admin account to make sure that there are no real accounts to delete (#42)
        - [ ] Fix the broken form behaviour with clearing fields on error (#43)
        - [ ] Update form to require email (#44)
        - [ ] Create migration deleting no-email accounts (#45)
        - [ ] Test the app still works end-to-end on dev server (#46)
        - [ ] Deploy email signup update to live server (#47)
    - [ ] Add account recovery via email (#48)
        - [ ] Add email delivery provider (#49)
            - [ ] Signup for Resend (#50)
            - [ ] Hook up resend to django mail backend (#51)
            - [ ] Add SPF, DKIM and DMARC records for the sending domain (#52)
        - [ ] Enable the django password reset routes (#53)
        - [ ] Style the reset pages and emails to match the app (#54)
        - [ ] Test a full reset against a real address (#55)
    - [ ] Add signup with Google option (#56)
        - [ ] Register for the service in Google cloud console (#57)
        - [ ] Add django-allauth and configure the provider (#58)
        - [ ] Decide what happens when a Google address matches an existing account (#59)

## Notifications

- [ ] Decide where a notification lives while the user is offline (#60)
- [ ] Deliver notifications over the existing websocket (#61)
- [ ] Send someone a room link without already sharing a room (#62)

## UI

- [x] Add app icon (favicon)
- [x] Add a landing page instead of just redirecting to login page right off the bat.
- [ ] UI rework (#63)
    - [ ] Restyle so the app does not read as default Bootstrap (#64)
    - [ ] Dark mode / Global styles (#65)

## Bots and demo traffic

- [ ] Script that signs up, logs in and drives a websocket (#66)
- [ ] Run it against a local container rather than the live server (#67)
- [ ] Chess bot that plays in its own room (#68)

## Infrastructure

- [x] Dockerize the application and add running instructions
- [x] Host the messenger
- [ ] Move to carrierpigeon.app (#69)
    - [ ] Register the domain (#70)
    - [ ] Point DNS at the VM (#71)
    - [ ] Update the Caddyfile for the new domain (#72)
    - [ ] Update ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS (#73)
    - [ ] Verify TLS is issued on the new domain (#74)
    - [ ] Redirect the duckdns domain at the new one (#75)
- [ ] Move the database to Postgres (#76)
- [ ] Move the VM to Debian trixie and update the Dockerfile base (#77)
- [ ] Secure redis so that it does not accept connections from other sources. (#78)
- [ ] Database backups (#79)
- [ ] Document the venv as editor support only (#80)
- [ ] Register the chat and accounts models in the django admin (#81)
- [ ] Bug: `scripts/setup.sh` creates the venv with `python3` rather than `python3.12` (#82)
