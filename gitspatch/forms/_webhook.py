from wtforms import Form, SelectField, StringField, validators

from gitspatch.services import InstalledRepository


def _coerce_github_repository(value: str) -> tuple[str, str, int]:
    owner, name, id = value.split(":")
    return owner, name, int(id)


class WebhookForm(Form):
    github_repository = SelectField(
        "Repository",
        validators=[validators.DataRequired()],
        coerce=_coerce_github_repository,
    )
    github_workflow_id = StringField(
        "Workflow ID", validators=[validators.DataRequired()]
    )

    def populate_github_repository(
        self, repositories: list[InstalledRepository]
    ) -> None:
        self.github_repository.choices = [
            (repository.form_value, repository.full_name) for repository in repositories
        ]
