---
name: liquibase-migrations
description: Create or update PostgreSQL schema and data migrations for Skill Swipe using Liquibase XML changelogs with inline SQL. Use for new changesets, schema changes, or loading reference data from CSV.
---

# Skill Swipe Liquibase migrations

- Use the task ID supplied by the user or established by the work context. For `SSK-2`, use `migrations/changelogs/ssk-2.xml`, `id="ssk-2"` for the tag changeset, and `tag="SSK-2"`. If the ID is missing from the request, check the active branch before asking.
- Append the XML file to `migrations/master.yaml` in dependency order. Use `file: changelogs/ssk-2.xml` and `relativeToChangelogFile: true`.
- Start each task changelog with a dedicated `tagDatabase` changeset. Put at least one SQL changeset after it. Use `author="skillswipe"`.
- In changeset IDs, separate the action, optional object type, and object name with hyphens. Use the exact database object name, keeping underscores between words in its name. Examples include `create-table-skill_synonyms`, `create-table-user_skills`, `create-schema-skillswipe`, and `insert-skill_synonyms`.
- Write inline `<sql>` and reverse SQL in `<rollback><sql>…</sql></rollback>`. Use plain XML text with escaping where required. Keep `preConditions`, CDATA, and `dbms` out of routine changesets.
- Choose SQL guards when the task calls for them. When `IF NOT EXISTS` can skip creation, account for the fact that a later rollback with `DROP` can still remove an object that existed before the migration.
- Preserve applied changesets, including their SQL, IDs, authors, and paths. If checksum validation fails, compare the current SQL with the applied version and restore the applied definition when it was changed in place. Put subsequent schema or data changes in new changesets.
- Check the XML, relative include, changeset order, and rollback. When local Docker is available and the task allows it, validate with `docker compose run --rm --build migrate validate`. Run `update` only when asked to apply the migration. Report any checks you could not run.

## Reference data from CSV

- Read the supplied versioned CSVs in `data/database/` and the changesets that define the destination tables. Check required values and duplicates against the destination keys. When a CSV foreign key points into another source file, verify that it resolves to a source row.
- Use one inline `INSERT` changeset per table, with an explicit column list and parent tables first. For skills and synonyms, put `insert-skills` and `insert-skill_synonyms` after the task tag, in that order.
- Omit PostgreSQL-generated primary keys from the insert columns. Use CSV IDs to link source rows while preparing the SQL. Resolve foreign keys in the SQL with a `SELECT` against a unique database key, such as `skills.name`.
- Escape single quotes for PostgreSQL and special characters for XML. Verify the generated rows against the source data, including the row counts and foreign key mapping.
- For rollback, delete the inserted rows by their data keys in reverse dependency order. Match synonyms by their parent skill, synonym text, and language.

```sql
INSERT INTO skills (name) VALUES ('Python');

INSERT INTO skill_synonyms (skill_id, synonym, lang) VALUES
    ((SELECT id FROM skills WHERE name = 'Python'), 'Python 3', 'en');
```

## Schema migration example

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
