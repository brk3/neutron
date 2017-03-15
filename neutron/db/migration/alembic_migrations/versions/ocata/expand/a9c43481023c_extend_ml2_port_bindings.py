# Copyright 2016 Intel Corporation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""extend_pk_with_host_and_add_status_to_ml2_port_binding

Revision ID: a9c43481023c
Revises: 5cd92597d11d
Create Date: 2016-11-22 11:48:43.479552

"""

# revision identifiers, used by Alembic.
revision = 'a9c43481023c'
down_revision = '929c968efe70'

from alembic import op
from oslo_db.sqlalchemy import ndb
from oslo_db.sqlalchemy import utils
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector as insp

from neutron.common import constants
from neutron.db import migration

MYSQL_ENGINE = 'mysql'
ML2_PORT_BINDING = 'ml2_port_bindings'
neutron_milestone = [migration.OCATA]


def upgrade():
    bind = op.get_bind()
    engine = bind.engine

    op.add_column(ML2_PORT_BINDING,
                  sa.Column('status',
                  sa.String(length=16),
                  nullable=False,
                  server_default=constants.PORT_BINDING_STATUS_ACTIVE))

    if (engine.name == MYSQL_ENGINE and
            not ndb.ndb_status(engine)):
        op.execute("ALTER TABLE ml2_port_bindings DROP PRIMARY KEY,"
                   "ADD PRIMARY KEY(port_id, host);")
    else:
        inspector = insp.from_engine(bind)
        fk_name = utils.get_foreign_key_constraint_name(engine,
                                                        'ml2_port_bindings',
                                                        'port_id')
        op.drop_constraint(fk_name, ML2_PORT_BINDING, type_='foreignkey')
        pk_constraint = inspector.get_pk_constraint(ML2_PORT_BINDING)
        op.drop_constraint(pk_constraint.get('name'), ML2_PORT_BINDING,
                           type_='primary')
        op.create_primary_key(op.f('pk_ml2_port_bindings'),
                              ML2_PORT_BINDING, ['port_id', 'host'])
        op.create_foreign_key(fk_name, ML2_PORT_BINDING, 'ports', ["port_id"],
                              ["id"], ondelete='CASCADE')


def expand_drop_exceptions():
    """
    Drop the existing primary key constraint and then extend it to include
    host as the primary key to support multiple bindings for the same port.
    This is needed to use drop in expand migration to pass test_branches.
    It is safe to recreate primary key in expand as it is backward compatible.
    """
    return {
        sa.Constraint: ['ml2_port_bindings_pkey']
    }
