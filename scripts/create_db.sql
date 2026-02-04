-- Create database and user for GEE-Flood (local development)
-- TODO: Run this via psql once Postgres is running.
-- Why it matters: explicit DB ownership shows data engineering responsibility.

CREATE USER geeflood_user WITH PASSWORD 'change_me';
CREATE DATABASE geeflood OWNER geeflood_user;
GRANT ALL PRIVILEGES ON DATABASE geeflood TO geeflood_user;
