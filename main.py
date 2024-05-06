import re
import redis
import json
import datetime

from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    ReferenceField,
    ListField,
    connect,
)

connect(db="my_database", host="localhost", port=27017)


class Author(Document):
    fullname = StringField(required=True)
    born_date = DateTimeField()
    born_location = StringField()
    description = StringField()


class Quote(Document):
    tags = ListField(StringField())
    author = ReferenceField(Author)
    quote = StringField()


r = redis.Redis(host="localhost", port=6379, db=0)


def parse_search_query(query):
    regex_name = re.compile(r"name:\s*(\w+(\s\w+)*)")
    regex_tag = re.compile(r"tag:\s*(\w+(\s\w+)*)")
    regex_short_name = re.compile(r"name:\s*(\w{2,})")
    regex_short_tag = re.compile(r"tag:\s*(\w{2,})")

    query = query.strip()

    search_name = regex_name.search(query)
    search_tag = regex_tag.search(query)
    search_short_name = regex_short_name.search(query)
    search_short_tag = regex_short_tag.search(query)

    if search_name or search_short_name:
        name_query = search_name.group(1) if search_name else search_short_name.group(1)
        return {"author__fullname__icontains": name_query}
    elif search_tag or search_short_tag:
        tag_query = search_tag.group(1) if search_tag else search_short_tag.group(1)
        return {"tags__icontains": tag_query}
    else:
        return None


def perform_mongo_search(query):
    filter_query = parse_search_query(query)
    if filter_query:
        author_name_query = filter_query.pop("author__fullname__icontains", None)
        if author_name_query:
            author = Author.objects(fullname__icontains=author_name_query).first()
            if author:
                quotes = Quote.objects(author=author, **filter_query)
                return quotes.to_json(indent=4)
            else:
                return "Author not found."
        else:
            quotes = Quote.objects(**filter_query)
            return quotes.to_json(indent=4)
    else:
        return "Invalid query"


def load_data():
    with open("authors.json", "r") as authors_file:
        authors_data = json.load(authors_file)
        for author_data in authors_data:
            author_name = author_data["fullname"]
            author = Author.objects(fullname=author_name).first()
            if not author:
                born_date_str = author_data["born_date"]
                born_date_iso = datetime.datetime.strptime(
                    born_date_str, "%B %d, %Y"
                ).strftime("%Y-%m-%d")
                author_data["born_date"] = born_date_iso

                author = Author(**author_data)
                author.save()

    with open("quotes.json", "r") as quotes_file:
        quotes_data = json.load(quotes_file)
        for quote_data in quotes_data:
            author_name = quote_data.pop("author")
            author = Author.objects(fullname__icontains=author_name).first()
            if not author:
                raise ValueError(f"Author '{author_name}' does not exist.")
            quote_data["author"] = author
            quote = Quote(**quote_data)
            quote.save()


def search_quotes(query):
    cached_result = r.get(query)
    if cached_result:
        return json.loads(cached_result)
    else:
        result = perform_mongo_search(query)
        r.setex(query, 3600, json.dumps(result))
        return result


def main():
    load_data()

    while True:
        command = input(
            "Введіть команду (наприклад, name:Steve Martin, tag:life, tags:life,live, або exit): "
        ).strip()

        if command == "exit":
            break

        if not re.match(r"(name|tag):\s*\w+(\s+\w+)*", command):
            print("Неправильний формат команди. Спробуйте ще раз.")
            continue

        result = search_quotes(command)

        print(result)


if __name__ == "__main__":
    main()
