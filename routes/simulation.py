from flask import Blueprint, request, jsonify
from models import Simulation
from db import db

simulation_bp = Blueprint('simulation_bp', __name__)

@simulation_bp.route('/', methods=['POST'])
def create_simulation():
    data = request.json
    sim = Simulation(
        field_id=data['field_id'],
        scenario_type=data['scenario_type'],
        result_summary=data.get('result_summary')
    )
    db.session.add(sim)
    db.session.commit()
    return jsonify({"message": "Simulation créée", "id": sim.id})

@simulation_bp.route('/', methods=['GET'])
def get_simulations():
    sims = Simulation.query.all()
    return jsonify([{
        "id": s.id,
        "field_id": s.field_id,
        "scenario_type": s.scenario_type,
        "result_summary": s.result_summary,
        "created_at": s.created_at
    } for s in sims])
