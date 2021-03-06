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

from neutron_lib.db import constants as db_const
from neutron_lib.db import model_base
from oslo_db.sqlalchemy.types import String
from sqlalchemy.dialects.mysql import TEXT
from sqlalchemy.dialects.mysql import TINYTEXT

import sqlalchemy as sa
from sqlalchemy import sql

from neutron.agent.common import utils


class Agent(model_base.BASEV2, model_base.HasId):
    """Represents agents running in neutron deployments."""

    __table_args__ = (
        sa.UniqueConstraint('agent_type', 'host',
                            name='uniq_agents0agent_type0host'),
        model_base.BASEV2.__table_args__
    )

    # L3 agent, DHCP agent, OVS agent, LinuxBridge
    agent_type = sa.Column(String(255, mysql_ndb_length=128), nullable=False)
    binary = sa.Column(String(255, mysql_ndb_type=TINYTEXT), nullable=False)
    # TOPIC is a fanout exchange topic
    topic = sa.Column(String(255, mysql_ndb_type=TINYTEXT), nullable=False)
    # TOPIC.host is a target topic
    host = sa.Column(sa.String(255), nullable=False)
    availability_zone = sa.Column(sa.String(255))
    admin_state_up = sa.Column(sa.Boolean, default=True,
                               server_default=sql.true(), nullable=False)
    # the time when first report came from agents
    created_at = sa.Column(sa.DateTime, nullable=False)
    # the time when first report came after agents start
    started_at = sa.Column(sa.DateTime, nullable=False)
    # updated when agents report
    heartbeat_timestamp = sa.Column(sa.DateTime, nullable=False)
    # description is note for admin user
    description = sa.Column(sa.String(db_const.DESCRIPTION_FIELD_SIZE))
    # configurations: a json dict string, I think 4095 is enough
    configurations = sa.Column(String(4095, mysql_ndb_type=TEXT),
                               nullable=False)
    # resource_versions: json dict, 8191 allows for ~256 resource versions
    #                    assuming ~32byte length "'name': 'ver',"
    #                    the whole row limit is 65535 bytes in mysql
    resource_versions = sa.Column(sa.String(8191))
    # load - number of resources hosted by the agent
    load = sa.Column(sa.Integer, server_default='0', nullable=False)

    @property
    def is_active(self):
        return not utils.is_agent_down(self.heartbeat_timestamp)
