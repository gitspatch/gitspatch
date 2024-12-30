from typing import cast

from wtforms import Form, SelectField, StringField, validators

from gitspatch.services import InstalledRepository


def _coerce_repository(value: str | list[str | int]) -> tuple[str, str, int]:
    if isinstance(value, list):
        return cast(tuple[str, str, int], tuple(value))
    owner, name, id = value.split(":")
    return owner, name, int(id)


class CreateWebhookFormStep1(Form):
    repository = SelectField(
        "Repository", validators=[validators.DataRequired()], coerce=_coerce_repository
    )

    def populate_repository(self, repositories: list[InstalledRepository]) -> None:
        self.repository.choices = [
            (repository.form_value, repository.full_name) for repository in repositories
        ]


class CreateWebhookFormStep2(Form):
    workflow_id = StringField(
        "Workflow ID",
        validators=[validators.DataRequired()],
        description='You can pass the workflow file name, like "CI.yml".',
    )


class EditWebhookForm(Form):
    workflow_id = StringField(
        "Workflow ID",
        validators=[validators.DataRequired()],
        description='You can pass the workflow file name, like "CI.yml".',
    )
