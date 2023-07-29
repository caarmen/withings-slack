error=0
for project in slackhealthbot alembic tests
do
  black $project || error=$?
  ruff check $project || error=$?
  isort --profile black $project || error=$?
done
exit $error
