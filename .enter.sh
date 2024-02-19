export PIP_REQUIRE_VIRTUALENV=true
export PIP_USER=false
if [[ -f .venv/bin/activate ]]; then
   export PYTHONPATH=$(readlink -f .)

   source .venv/bin/activate
fi
