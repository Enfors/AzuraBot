#!/usr/bin/env python3.7

import asyncio

import motor.motor_asyncio


async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

    # Create instance of AsyncIOMotorClient
    client = motor.motor_asyncio.AsyncIOMotorClient()

    # Get a database
    db = client["test_database"] # client.test_database works too

    # Getting a collection
    collection = db["todos"] # db.todos works too

    # Inserting
    document = {"name": "Water flowers"}
    result = await db.todos.insert_one(document)
    print(f"Result {result.inserted_id}")


asyncio.run(main())
