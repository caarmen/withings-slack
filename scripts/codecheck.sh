for project in withingsslack
do
  black $project
  ruff check $project
done
