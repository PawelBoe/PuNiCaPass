import argparse
from datetime import datetime
import json

from Crypto import generate_new_keypair, json_to_qrcode, smallSign, smallVerify
from Models import NumericalValues, OrganizationKeys, RevokedPasses, db
from flask import Flask, jsonify, render_template, request, send_file


def initialize_db():
    print(
        """(re)initializing database, all previously created data is now lost and all PuNiCa Passes invalid!"""
    )
    db.connect()

    db_models = [
        NumericalValues,
        OrganizationKeys,
        RevokedPasses,
    ]

    db.drop_tables(db_models)
    db.create_tables(db_models)

    NumericalValues.create(label="PassIdCounter")

    organizations = ["Nil", "Casino", "Pub"]

    for organization in organizations:
        password = input(f"provide a password for {organization}: ")
        pub_key, priv_key = generate_new_keypair(password)
        OrganizationKeys.create(
            organization_name=organization,
            public_key_b64=pub_key,
            private_key_b64=priv_key,
        )

    db.close()


def start_app(admin_token):
    print("starting webapp and api backend")
    db.connect()
    app = Flask(__name__)

    @app.route("/")
    def landing_page():
        return render_template("index.html")

    @app.route("/page/pass/organizations", methods=["GET"])
    def page_pass_organizations():
        # provide whole list of organization names and public keys
        query = OrganizationKeys.select()
        data = {
            "organizations": [(o.organization_name, o.public_key_b64) for o in query]
        }
        return jsonify(data)

    @app.route("/page/pass/revoked", methods=["GET"])
    def page_pass_revoked():
        # provide whole list of revoked pass ids
        query = RevokedPasses.select()
        data = {"revoked_passes": [revokedPass.pass_id for revokedPass in query]}
        return jsonify(data)

    @app.route("/page/pass/counter", methods=["GET"])
    def page_pass_counter():
        # provide number of issued passes
        passIdCounter = NumericalValues.get(label="PassIdCounter")
        data = {"PassIdCounter": passIdCounter.value}
        return jsonify(data)

    @app.route("/page/pass/sign", methods=["GET"])
    def page_pass_sign():
        # provide user data, admin token and key data form
        # submit user data to api with admin token and key data
        # get and display pass pdf/png response
        return render_template("sign.html")

    @app.route("/page/pass/verify", methods=["GET"])
    def page_pass_verify():
        # provide qr code scanner for pass data
        # submit pass data to api
        # get pass status message
        return render_template("verify.html")

    @app.route("/page/pass/revoke", methods=["GET"])
    def page_pass_revoke():
        # provide pass_data form
        # submit pass data to api with admin token
        # get revoked pass status message
        return render_template("revoke.html")

    def parseSignArguments(form):
        args = {}
        args["name"] = form["name"]
        args["comment"] = form.get("comment", "")
        args["entryDate"] = form["entryDate"]  # TODO parse date properly
        args["adminToken"] = form["adminToken"]
        args["memberNil"] = "memberNil" in form
        args["memberCasino"] = "memberCasino" in form
        args["memberPub"] = "memberPub" in form
        return args

    @app.route("/api/pass/sign", methods=["POST"])
    def api_pass_sign():
        # test admin token
        # sign pass data with key of key data and new pass id
        # increment PassIdCounter
        # create qr code
        # (TODO merge qr code with pass image)
        # reply with qr/pass image

        f = request.files["image"]
        f.save("someImage.png")

        args = {}
        try:
            args = parseSignArguments(request.form)
        except Exception as e:
            return jsonify(
                {
                    "status": "not ok",
                    "detail": "parsing arguments failed {}".format(str(e)),
                }
            )

        if args["adminToken"] != admin_token:
            return jsonify(
                {
                    "status": "not ok",
                    "detail": "unauthorized: bad Admin-Token",
                }
            )

        # signed data
        PassIdCounter = NumericalValues.get(label="PassIdCounter")
        passId = PassIdCounter.value
        issue_date = datetime.now().strftime("%m/%d/%Y")
        name = args["name"]
        comment = args["comment"]
        entryDate = args["entryDate"]
        memberNil = "N" if args["memberNil"] else ""
        memberCasino = "C" if args["memberCasino"] else ""
        memberPub = "P" if args["memberPub"] else ""
        unsigned_data = f"{passId};{name};{comment};{entryDate};{memberNil}{memberCasino}{memberPub};{issue_date}"

        # FIXME do not use organizations!
        # private_key = OrganizationKeys.get(organization_name="Nil").private_key_b64
        try:
            # signed_data = sign(private_key, "asdf", unsigned_data)
            signed_data = smallSign(unsigned_data, "asdf")
        except Exception as e:
            return jsonify(
                {
                    "status": "not ok",
                    "detail": f"signing failed: {str(e)}",
                }
            )

        PassIdCounter.value += 1
        PassIdCounter.save()

        qr_code = json_to_qrcode(signed_data)
        # FIXME do not save temporary image, send from memory
        qr_code.save("tmp.png")
        return send_file("tmp.png", mimetype="image/png")

    @app.route("/api/pass/verify", methods=["POST"])
    def api_pass_verify():
        # test revoked list for pass data
        # verify signed pass data
        # reply with result

        data_json = json.loads(request.data)

        pass_id = int(data_json["data"].split(";")[0])
        # membership = data_json["data"].split(";")[2]
        # public_key = OrganizationKeys.get(organization_name=membership).public_key_b64

        revoked = (
            len(RevokedPasses.select().where(RevokedPasses.pass_id == pass_id)) > 0
        )
        if revoked:
            return (
                jsonify(
                    {
                        "status": "not ok",
                        "detail": "pass is revoked",
                        "data": data_json["data"],
                    }
                ),
                200,
            )

        # if verify(data_json, public_key):
        if smallVerify(data_json, "asdf"):
            return (
                jsonify(
                    {
                        "status": "ok",
                        "detail": "verification succesfull",
                        "data": data_json["data"],
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "status": "not ok",
                    "detail": "verification failed",
                    "data": data_json["data"],
                }
            ),
            200,
        )

    @app.route("/api/pass/revoke", methods=["POST"])
    def api_pass_revoke():
        # test admin token
        # add pass id to revoked list
        # reply with ok/not ok page
        # TODO add remove from revoked list capability?
        # TODO Revoke based on name, hide name in db via hash

        token = request.form["admin_token"]

        if token != admin_token:
            return jsonify(
                {
                    "status": "not ok",
                    "detail": "unauthorized",
                }
            )
        try:
            pass_id = int(request.form["pass_id"])
        except ValueError:
            return jsonify(
                {
                    "status": "not ok",
                    "detail": "provided pass_id is not a number",
                }
            )

        RevokedPasses.create(pass_id=pass_id)
        return jsonify(
            {
                "status": "ok",
                "detail": f"pass id '{request.form['pass_id']}' was added to revoked list",
            }
        )

    # FIXME get proper CA certificate?
    # FIXME error handling if certificate missing
    app.run(ssl_context=("cert.pem", "key.pem"), debug=True, host="0.0.0.0")
    db.close()


def main():
    parser = argparse.ArgumentParser(
        "Create and manage member certificates for PuNiCa Pass"
    )
    parser.add_argument("--initialize", action="store_true")
    parser.add_argument("--admin_token", required=True)
    args = parser.parse_args()

    if args.initialize:
        initialize_db()
    else:
        start_app(args.admin_token)


if __name__ == "__main__":
    main()
