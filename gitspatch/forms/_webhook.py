from wtforms import Form, SelectField, StringField, validators

from gitspatch.services import InstalledRepository


def _coerce_repository(value: str) -> tuple[str, str, int]:
    owner, name, id = value.split(":")
    return owner, name, int(id)


class CreateWebhookForm(Form):
    repository = SelectField(
        "Repository", validators=[validators.DataRequired()], coerce=_coerce_repository
    )
    workflow_id = StringField(
        "Workflow ID",
        validators=[validators.DataRequired()],
        description='You can pass the workflow file name, like "CI.yml".',
    )

    def populate_repository(self, repositories: list[InstalledRepository]) -> None:
        self.repository.choices = [
            (repository.form_value, repository.full_name) for repository in repositories
        ]


class EditWebhookForm(Form):
    workflow_id = StringField(
        "Workflow ID",
        validators=[validators.DataRequired()],
        description='You can pass the workflow file name, like "CI.yml".',
    )
