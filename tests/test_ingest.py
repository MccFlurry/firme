import json

from engine.ingest import parse


def _json(payload):
    return json.dumps(payload, ensure_ascii=False)


def test_unknown_english_and_accented_columns_map():
    rows = [
        {"customer": "Ana Quispe", "phone_number": "912345678", "monthly_price": "79.90",
         "plan_name": "Fibra 200", "label": "buena"},
        {"customer": "Luis Paredes", "teléfono": "923456789", "precio": "50.00",
         "plan": "fibra_400", "etiqueta": "mala"},
    ]
    sales, report = parse(_json(rows))
    assert len(sales) == 2
    assert report.mapped["customer"] == "customer_name"
    assert report.mapped["phone_number"] == "phone"
    assert report.mapped["monthly_price"] == "price"
    assert report.mapped["plan_name"] == "plan"
    assert report.mapped["teléfono"] == "phone"
    assert report.mapped["precio"] == "price"
    assert sales[0].customer_name == "Ana Quispe"
    assert sales[0].phone == "912345678"
    assert sales[0].price == 79.90
    assert sales[0].plan == "Fibra 200"
    assert sales[0].label == "buena"
    assert sales[1].label == "mala"


def test_junk_column_goes_to_unrecognized_and_extra():
    sales, report = parse(_json([{"customer": "Ana", "column_basura": "x", "phone": "912345678"}]))
    assert report.unrecognized == ["column_basura"]
    assert sales[0].extra["column_basura"] == "x"
    assert sales[0].customer_name == "Ana"


def test_csv_and_json_give_same_result():
    rows = [{"customer": "Ana Quispe", "phone_number": "912345678", "monthly_price": "79.90",
             "plan_name": "Fibra 200", "label": "buena"}]
    from_json, report_json = parse(_json(rows))
    csv_text = "customer,phone_number,monthly_price,plan_name,label\nAna Quispe,912345678,79.90,Fibra 200,buena\n"
    from_csv, report_csv = parse(csv_text)
    assert report_json.mapped == report_csv.mapped
    assert from_json[0].model_dump() == from_csv[0].model_dump()


def test_corrupt_row_does_not_kill_batch():
    csv_text = (
        "customer,phone_number,monthly_price,plan_name,label\n"
        "Ana Quispe,912345678,79.90,Fibra 200,buena\n"
        "fila rota con distinto numero de columnas\n"
        "Luis Paredes,923456789,50.00,Fibra 400,mala\n"
    )
    sales, report = parse(csv_text)
    assert len(sales) == 2
    assert any("columnas" in error for error in report.errors)


def test_label_normalization_and_missing_fields():
    sales, report = parse(_json([{"customer": "Ana", "phone": "912345678", "label": "1"}]))
    assert sales[0].label == "buena"
    assert "plan" in report.missing
    assert "price" in report.missing


def test_ventas_wrapper_and_dict_list_input():
    sales, report = parse(_json({"ventas": [{"customer": "Ana", "phone": "912345678"}]}))
    assert len(sales) == 1
    assert sales[0].customer_name == "Ana"
    sales, report = parse([{"customer": "Luis", "phone": "923456789"}])
    assert len(sales) == 1
    assert sales[0].customer_name == "Luis"
