for project in withingsslack alembic
do
  black $project
  ruff check $project
done
