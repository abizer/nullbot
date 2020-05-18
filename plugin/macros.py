import asyncpg
import re

from functools import partial
from nio import RoomMessageText
from nio.responses import RoomResolveAliasError
from asyncpg.exceptions import UniqueViolationError


macros_get_re = re.compile(r'#m (\w+)$')
macros_add_re = re.compile(r'^#m add (\w+) (.+)$')
macros_rm_re  = re.compile(r'^#m rm (\w+)$')
macros_mv_re  = re.compile(r'^#m mv (\w+) (\w+)$')
macros_update_re  = re.compile(r'^#m update (\w+) (.+)$')

KEYWORDS = ('add', 'rm', 'mv', 'update')

async def register(bot):
    bot.client.add_event_callback(partial(macros_cb, bot), RoomMessageText)
    

async def macros_cb(bot, room, event):
    conn = bot.pgc

    # Find a macro from the database
    if (match := macros_get_re.fullmatch(event.body)):
        slug = match.group(1)
        get_query = "SELECT link FROM macros WHERE slug = $1"

        try:
            macro = await conn.fetchrow(get_query, slug)
            if macro:
                await bot.send_room(room, macro['link'])
            else:
                await bot.send_room(room, f"Macro `{slug}` not found.")
        except Exception as e:
            await bot.send_room(room, str(e))
            print(e)
        
    # Add a new macro to the database
    elif (match := macros_add_re.fullmatch(event.body)):
        slug = match.group(1)
        link = match.group(2)

        if slug in KEYWORDS:
            await bot.send_room(room, f"Macro `{slug}` contains illegal keyword")
            return

        insert_query = "INSERT INTO macros (slug, link) VALUES ($1, $2);"

        try:
            await conn.execute(insert_query, slug, link)
            await bot.send_room(room, f"Added macro `{slug}`")
        except UniqueViolationError as ue:
            await bot.send_room(room, f'Macro {slug} already exists')
        except Exception as e:
            await bot.send_room(room, str(e))

    # Delete a macro
    elif (match := macros_rm_re.fullmatch(event.body)):
        slug = match.group(1)

        rm_query = "DELETE FROM macros WHERE slug = $1;"
        
        await conn.execute(rm_query, slug)
        await bot.send_room(room, f"Deleted macro `{slug}`")

    # Rename a macro
    elif (match := macros_mv_re.fullmatch(event.body)):
        old_slug = match.group(1)
        new_slug = match.group(2)

        mv_query = "UPDATE macros SET slug = $2 WHERE slug = $1;"

        try:
            await conn.execute(mv_query, old_slug, new_slug)
            await bot.send_room(room, f"Macro `{old_slug}` moved to `{new_slug}`")
        except UniqueViolationError as ue:
            await bot.send_room(room, f"Macro {new_slug} already exists")
        except Exception as e:
            await bot.send_room(room, str(e))
        
    # Change the link a macro slug points to
    elif (match := macros_update_re.fullmatch(event.body)):
        slug = match.group(1)
        new_link = match.group(2)

        update_query = "UPDATE macros SET link = $2 WHERE slug = $1;"

        await conn.execute(update_query, slug, new_link)
        await bot.send_room(room, f"Macro `{slug}` updated")
