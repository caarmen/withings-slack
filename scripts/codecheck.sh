for project in withingsslack alembic tests
do
  black $project
  ruff check $project
done
