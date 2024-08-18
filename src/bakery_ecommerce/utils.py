def get_model_dict(model):
    return dict(
        (column.name, getattr(model, column.name)) for column in model.__table__.columns
    )
