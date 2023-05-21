for project in slackhealthbot alembic tests
do
  black $project
  ruff check $project
  isort $project
done
