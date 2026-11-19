---
name: liquibase-migrations
description: Create or update PostgreSQL schema and data migrations for Skill Swipe using Liquibase XML changelogs with inline SQL. Use when a task calls for a database migration or a new Liquibase changeset.
---

# Skill Swipe Liquibase migrations

- Use the task ID supplied by the user or established by the work context. For `SSK-2`, use `migrations/changelogs/ssk-2.xml`, `id="ssk-2"` for the tag changeset, and `tag="SSK-2"`. If the ID is missing from the request, check the active branch before asking.
- Append the XML file to `migrations/master.yaml` in dependency order. Use `file: changelogs/ssk-2.xml` and `relativeToChangelogFile: true`. Keep previously applied changesets and their paths intact.
- Start each task changelog with a dedicated `tagDatabase` changeset. Put at least one SQL changeset after it. Use `author="skillswipe"` and action-object IDs such as `create-table-outbox_petrailer` and `create-schema-skillswipe`.
- Write inline `<sql>` and reverse SQL in `<rollback><sql>…</sql></rollback>`. Use plain XML text with escaping where required. Keep `preConditions`, CDATA, and `dbms` out of routine changesets.
- Choose SQL guards when the task calls for them. When `IF NOT EXISTS` can skip creation, account for the fact that a later rollback with `DROP` can still remove an object that existed before the migration.
- Check the XML, relative include, changeset order, and rollback. When the local Docker environment is available, validate with `docker compose run --rm --build migrate validate`. Report any checks you could not run.

## Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-5.0.xsd">

    <changeSet id="ssk-2" author="skillswipe">
        <tagDatabase tag="SSK-2"/>
    </changeSet>

    <changeSet id="create-schema-skillswipe" author="skillswipe">
        <sql>
            CREATE SCHEMA IF NOT EXISTS skillswipe;
        </sql>
        <rollback>
            <sql>
                DROP SCHEMA skillswipe;
            </sql>
        </rollback>
    </changeSet>

</databaseChangeLog>
```
